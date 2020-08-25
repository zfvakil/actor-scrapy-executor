from shanghai.tools import ensure_dir

SCRAPED_IMG_META_LABELS: str = "domains_data/imgs/meta_labels_scraped"

IMG_META_LABELS_MODEL_EXPORT: str = "domains_data/imgs/meta_labels_model_export"

META_LABELS_PRED_MUSE_EXPORT: str = "domains_data/imgs/meta_labels_pred_muse_export"

ensure_dir(directory=SCRAPED_IMG_META_LABELS + "/")
ensure_dir(directory=IMG_META_LABELS_MODEL_EXPORT + "/")
ensure_dir(directory=META_LABELS_PRED_MUSE_EXPORT + "/")
