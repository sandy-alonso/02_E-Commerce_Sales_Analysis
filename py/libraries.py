import kagglehub
import shutil

path = kagglehub.dataset_download("thedevastator/unlock-profits-with-e-commerce-sales-data")
shutil.copytree(path, "../data/raw", dirs_exist_ok=True)
print("Data downloaded and copied to ../data/raw")
