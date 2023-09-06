import logging
import joblib
from pandas import DataFrame

logger = logging.getLogger(__name__)


class Filter:
    PREDICT_COL_NAME = "y_predict"

    def __init__(self, model_filename: str):
        self.model_filename = model_filename

        logger.info(f"Loading model from {self.model_filename}.")
        self.model = joblib.load(self.model_filename)
        logger.info(f"Successfully loaded model from `{self.model_filename}`.")

    def predict(self, variants: DataFrame, binary_labels: bool) -> DataFrame:
        variants_subset = variants.drop(columns=[
            "chrom", "pos", "ref", "alts", "b64encode", "filter", "any_pub", "is_pzm",
            "rpa_ref", "rpa_alt", "strq", "gc"
        ])

        y_predict = self.model.predict(variants_subset)
        variants[self.PREDICT_COL_NAME] = y_predict

        if not binary_labels:
            variants[self.PREDICT_COL_NAME] = variants[self.PREDICT_COL_NAME].map({0: "Not_PZM", 1: "PZM"})
        return variants
