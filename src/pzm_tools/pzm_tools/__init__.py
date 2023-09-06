import argparse
import logging
import os

from .modules.filter import Filter
from .modules.parser import Parser


logger = logging.getLogger(__name__)


def call_filter(model_filename: str, vcf_filename: str, binary_labels: bool):
    parser = Parser()
    variants_df = parser.read_vcf(vcf_filename)

    pzm_filter = Filter(model_filename)

    logger.info(f"Start predicting classification for {len(variants_df)} variants.")
    variants_df_predict = pzm_filter.predict(variants_df, binary_labels)
    logger.info(f"Obtained predictions for {len(variants_df_predict)} variants.")

    directory, filename = os.path.split(vcf_filename)
    basename, ext = os.path.splitext(filename)
    if ext == ".gz":
        basename, _ = os.path.splitext(basename)
    output_filename = os.path.join(directory, f"predict_{basename}.csv")

    logger.info(f"Start serializing the parsed variants and their predictions to `{output_filename}`")
    variants_df_predict.to_csv(output_filename)
    logger.info(f"Finished serialization to `{output_filename}`.")


def main():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.DEBUG)

    parser = argparse.ArgumentParser(
        description="Tools for studying PZM variants")

    subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

    add_parser = subparsers.add_parser(
        "label",
        help="Label the variants in a given VCF file as PZM or not-PZM using a trained random forest model.")
    add_parser.add_argument("model_filename", type=str, help="File storing a saved random forest model.")
    add_parser.add_argument("vcf_filename", type=str, help="Input VCF filename")
    add_parser.add_argument(
        "--binary-labels", "-b", action="store_true",
        help="If set, labels predictions `0` and `1` instead of their default equivalents "
             "`Not PZM` and `PZM` respectively.")
    add_parser.set_defaults(func=call_filter)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args_dict = vars(args)
        subcmd = args_dict.pop("subcommand")
        func = args_dict.pop("func")
        logger.info(f"Received arguments: {args_dict}")
        func(**args_dict)
        logger.info(f"Successfully finished executing the `{subcmd}` subcommand.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
