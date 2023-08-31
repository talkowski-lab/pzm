import logging
import base64
import pandas as pd
import numpy as np
import math

from dataclasses import dataclass
from pandas import DataFrame
from pybedtools import BedTool
from pysam import VariantFile
from sklearn.preprocessing import MinMaxScaler
from typing import Any, Callable, List, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Mapper:
    is_sample_metric: bool
    default: dict
    func: Callable[[Any], dict]
    output_keys: List[str]


class Parser:

    def __init__(self):
        self.no_repeat_masker_key = "no_repeat_masker"
        self.b64encode_col = "b64encode"
        self.rmcl_values = [
            "DNA", "DNA?", "LINE", "LTR", "LTR?", "Low_complexity", "RC", "RC?", "RMCL", "RNA", "Retroposon",
            "SINE", "SINE?", "Satellite", "Simple_repeat", "Unknown", "rRNA", "scRNA", "snRNA", "srpRNA",
            "tRNA", self.no_repeat_masker_key
        ]
        self.rmcl_dict = {self.rmcl_values[i]: i for i in range(len(self.rmcl_values))}

        # INFO fields (contains both per-sample and per-site metrics)
        self.info_fields = {
            # Phred-scaled quality that alt alleles are not germline variants
            "GERMQ": Mapper(True, {}, lambda x: {"GERMQ": int(x)}, ["GERMQ"]),

            # median base quality by allele
            "MBQ": Mapper(True, {}, lambda x: {"MBQ_ref": int(x[0]), "MBQ_alt": int(x[1])}, ["MBQ_ref", "MBQ_alt"]),

            # median fragment length by allele
            "MFRL": Mapper(True, {}, lambda x: {"MFRL_ref": int(x[0]), "MFRL_alt": int(x[1])},
                           ["MFRL_ref", "MFRL_alt"]),

            # median mapping quality by allele
            "MMQ": Mapper(True, {}, lambda x: {"MMQ_ref": int(x[0]), "MMQ_alt": int(x[1])}, ["MMQ_ref", "MMQ_alt"]),

            # median distance from end of read
            "MPOS": Mapper(True, {}, lambda x: {"MPOS": int(x[0])}, ["MPOS"]),

            # Normalized, Phred-scaled likelihoods for genotypes as defined
            # in the VCF specification
            "PL": Mapper(True, {}, lambda x: {"PL": int(x)}, ["PL"]),

            # Log 10 likelihood ratio score of variant existing versus not existing
            "TLOD": Mapper(True, {}, lambda x: {"TLOD": float(x[0])}, ["TLOD"]),

            "all_cohort_af": Mapper(False, {}, lambda x: {"all_cohort_af": float(x[0])}, ["all_cohort_af"]),

            # Number of events in this haplotype
            "ECNT": Mapper(False, {}, lambda x: {"ECNT": int(x)}, ["ECNT"]),

            # Genotype Quality
            # The GC percent track shows the percentage of G (guanine)
            # and C (cytosine) bases in 5-base windows. High GC content
            # is typically associated with gene-rich areas.
            "GC": Mapper(False, {}, lambda x: {"GC": float(max(x))}, ["GC"]),

            # If present, site occurs in a low complexity region
            "LCR": Mapper(False, {"LCR": False}, lambda x: {"LCR": True}, ["LCR"]),

            # Frequency of PASS alleles in the cohort run with the same PON
            "pass_cohort_AF": Mapper(False, {}, lambda x: {"pass_cohort_AF": float(x)}, ["pass_cohort_AF"]),

            # negative log 10 population allele frequencies of alt alleles
            "POPAF": Mapper(False, {}, lambda x: {"POPAF": float(x[0])}, ["POPAF"]),

            # Repeat Masker class
            "RMCL": Mapper(False, {"RMCL": self.get_rmcl_encoding((self.no_repeat_masker_key,))},
                           lambda x: {"RMCL": self.get_rmcl_encoding(x)}, ["RMCL"]),

            # Number of times tandem repeat unit is repeated,
            # for each allele (including reference)
            "RPA": Mapper(False, {}, lambda x: {"RPA_ref": int(x[0]), "RPA_alt": int(x[1])}, ["RPA_ref", "RPA_alt"]),

            # If present, site occurs in a segmental duplication region
            "SEGDUP": Mapper(False, {"SEGDUP": False}, lambda x: {"SEGDUP": True}, ["SEGDUP"]),

            # If present, site occurs in a simple repeat region
            "SIMPLEREP": Mapper(False, {"SIMPLEREP": False}, lambda x: {"SIMPLEREP": True}, ["SIMPLEREP"]),

            # Variant is a short tandem repeat
            "STR": Mapper(False, {"STR": False}, lambda x: {"STR": True}, ["STR"]),

            # Phred-scaled quality that alt alleles in STRs are not
            # polymerase slippage errors
            "STRQ": Mapper(False, {}, lambda x: {"STRQ": int(x)}, ["STRQ"]),

            # If present, site occurs in the broad exome evaluation region
            "WESREG": Mapper(False, {"WESREG": False}, lambda x: {"WESREG": True}, ["WESREG"])
        }

        # FORMAT fields (contains both per-sample and per-site metrics)
        self.genotype_fields = {
            # Allelic depths for the ref and alt alleles in the order listed
            "AD": Mapper(True, {}, lambda x: {"AD_ref": int(x[0]), "AD_alt": int(x[1])}, ["AD_ref", "AD_alt"]),

            # Allele fractions of alternate alleles in the tumor
            "AF": Mapper(True, {}, lambda x: {"AF": float(x[0])}, ["AF"]),

            # Approximate read depth (reads with MQ=255 or with bad mates are filtered)
            "DP": Mapper(True, {}, lambda x: {"DP": int(x)}, ["DP"]),

            # Count of fragments supporting each allele.
            "FAD": Mapper(True, {}, lambda x: {"FAD_ref": int(x[0]), "FAD_alt": int(x[1])}, ["FAD_ref", "FAD_alt"]),

            # Genotype Quality
            "GQ": Mapper(True, {}, lambda x: {"GQ": int(x)}, ["GQ"]),

            # 0: phased (e.g., 1|0 or 0|1)
            # 1: unphased (e.g., 0/1)
            "GT": Mapper(True, {}, lambda x: {"GT": 0 if "|" in x else 1}, ["GT"]),

            # "Per-sample component statistics which comprise the Fisher's
            # exact test to detect strand bias."
            "SB": Mapper(True, {}, lambda x: {"SOR": self.get_sor(x)}, ["SOR"]),

            # # Count of reads in F1R2 pair orientation supporting each allele
            # "F1R2": lambda x: {"F1R2_allele_a": float(x[0]), "F1R2_allele_b": float(x[1])},

            # # Count of reads in F2R1 pair orientation supporting each allele
            # "F2R1": lambda x: {"F2R1_allele_a": float(x[0]), "F2R1_allele_b": float(x[1])},
        }

    def get_one_hot_rmcl_encoding(self, rmcl):
        one_hot = np.zeros((len(self.rmcl_dict),))
        one_hot[self.rmcl_dict[rmcl]] = 1
        return one_hot

    def get_rmcl_encoding(self, rmcl: Tuple[str, ...]):
        one_hot_sequence = [self.get_one_hot_rmcl_encoding(x) for x in rmcl]
        one_hot_array = np.array(one_hot_sequence)

        # Get the index of the maximum value in each row
        row_max_index = np.argmax(one_hot_array, axis=1)

        # Convert the row indices to a single number
        number = np.sum(row_max_index * (len(self.rmcl_dict) ** np.arange(len(row_max_index))))

        return number

    @staticmethod
    def get_sor(sb):
        ref_fw = sb[0] + 1
        ref_rv = sb[1] + 1
        alt_fw = sb[2] + 1
        alt_rv = sb[3] + 1
        symmetrical_ratio = (ref_fw * alt_rv) / (alt_fw * ref_rv) + (alt_fw * ref_rv) / (ref_fw * alt_rv)
        ref_ratio = ref_rv / ref_fw
        alt_ratio = alt_fw / alt_rv
        sor = math.log(symmetrical_ratio) + math.log(ref_ratio) - math.log(alt_ratio)
        return sor

    # Generate a base64 encoding of variant identifier fields in order to better match variants across samples.
    @staticmethod
    def get_var_base64_encoding_row(row):
        return Parser.get_var_base64_encoding(row["chr"], row["hg38_pos"], row["ref"], (row["alt"],))

    @staticmethod
    def get_var_base64_encoding(chrom: str, pos: int, ref: str, alts: Tuple[str, ...]) -> str:
        id_phrase = "_".join([chrom.lower().replace("chr", ""), str(pos), ref, *[x for x in alts]])
        b64encode = base64.b64encode(id_phrase.encode("utf-8")).decode("utf-8")
        return b64encode

    def parse_variant(self, variant, mappers):
        b64encode = self.get_var_base64_encoding(variant.chrom, variant.pos, variant.ref, variant.alts)

        # TEMP disabled since this is not currently developed to support preparing data for training
        # mvv: molecularly validated variant
        mvv = None  # validated_var_dict.get(b64encode)

        metrics = {
            "chrom": variant.chrom,
            "pos": variant.pos,
            "ref": variant.ref,
            "alts": variant.alts,
            self.b64encode_col: b64encode,
            "filter": ";".join(x for x in variant.filter.keys()),
            "any_pub": mvv.any_pub if mvv is not None else np.nan
        }

        is_validated_pzm_key = "is_pzm"
        metrics[is_validated_pzm_key] = np.nan
        # mvv.is_pzm if mvv is not None and mvv.sample_id == sample_id else np.nan

        for k, mapper in mappers.items():
            if k in self.info_fields and k in variant.info:
                x = mapper.func(variant.info.get(k))
            elif k in self.genotype_fields and k in variant.samples[0]:
                x = mapper.func(variant.samples[0][k])
            else:
                x = mapper.default

            metrics.update(x)

        # True: the variant is SNV
        # False: the variant is Indel
        metrics["is_snv"] = True if len(variant.ref) == len(variant.alts) else False

        return metrics

    def get_variants_df(self, vcf_filename: str) -> DataFrame:
        vcf = VariantFile(vcf_filename)
        parsed_metrics = []

        mappers = {**self.info_fields, **self.genotype_fields}

        for variant in vcf:
            parsed_metrics.append(self.parse_variant(variant, mappers))

        metrics_df = pd.DataFrame(parsed_metrics)
        metrics_df = metrics_df.rename(columns={x: x.lower() for x in metrics_df.columns})
        return metrics_df

    def get_normalized_df(self, metrics: DataFrame) -> DataFrame:
        metrics_ndf = metrics  # .copy()

        no_norm_cols = [
            "chrom", "pos", "ref", "alts", "b64encode", "filter", "any_pub", "is_molecularly_validated_pzm"
        ]

        # Get a list of site metrics, and exclude them from normalization.
        # We do not want to normalize these metrics, at least at a per-sample basis.
        for _, v in self.genotype_fields.items():
            if not v.is_sample_metric:
                no_norm_cols.extend(v.output_keys)

        # Do not normalize boolean columns
        no_norm_cols.extend(metrics_ndf.select_dtypes(include="bool").columns.tolist())

        mm_scaler = MinMaxScaler()
        cols = np.setdiff1d(metrics_ndf.columns.to_numpy(), no_norm_cols)
        metrics_ndf[cols] = mm_scaler.fit_transform(metrics_ndf[cols])

        return metrics_ndf

    @staticmethod
    def get_filtered_df(df: DataFrame, blacklist_regions_filename: str = None) -> DataFrame:
        af_condition = df["af"] >= 0.3675
        simplerep_condition = df["simplerep"] == True
        segdup_condition = df["segdup"] == True

        condition = df["is_pzm"].isna() & (af_condition | simplerep_condition | segdup_condition)

        df = df[~condition]

        blacklist_regions = [
            {"chr": "chr14", "start": 105586437, "end": 106879844},
            {"chr": "chr2", "start": 88857361, "end": 90235368},
            {"chr": "chr22", "start": 22026076, "end": 22922913},
            {"chr": "chr6", "start": 28510120, "end": 33480577},
        ]

        def assert_overlap(row):
            for br in blacklist_regions:
                if row["chrom"] == br["chr"] and br["start"] <= row["pos"] <= br["end"]:
                    return True
            return False

        overlap_mask = df.apply(assert_overlap, axis=1)
        df = df[~overlap_mask]

        if blacklist_regions_filename is not None:
            blacklist_regions_bed = BedTool(blacklist_regions_filename)

            tmp_input_df = df.copy()
            tmp_input_df = tmp_input_df[["chrom", "pos"]]
            tmp_input_df["end"] = tmp_input_df["pos"] + 1
            tmp_input_df["tmp_val"] = 0

            tmp_bed = BedTool.from_dataframe(tmp_input_df)
            intersect_result = blacklist_regions_bed.intersect(tmp_bed)
            intersect_result_df = intersect_result.to_dataframe()

            df = df.merge(
                intersect_result_df,
                left_on=["chrom", "pos"], right_on=["chrom", "start"], how="left", indicator=True)

            df = df.drop(df[df["_merged"] == "both"])
            df = df.drop(["start", "end", "_merge"], axis=1)

        return df

    def read_vcf(
            self, vcf_filename: str, normalize: bool = True,
            hard_filter: bool = True, blacklist_regions_filename: str = None) -> DataFrame:
        metrics_df = self.get_variants_df(vcf_filename)

        if normalize:
            metrics_df = self.get_normalized_df(metrics_df)

        if hard_filter:
            metrics_df = self.get_filtered_df(metrics_df, blacklist_regions_filename)

        return metrics_df
