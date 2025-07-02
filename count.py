import os
#numara imaginile din fiecare categorie de tip de ten, din fiecare subset al setului de date
dataset_path = "/Users/alexiaserban/Downloads/skin_types" 
# Lista cu subfolderele principale
splits = ["train", "valid", "test"]

for split in splits:
    print(f"\n📁 {split.upper()}:")

    split_path = os.path.join(dataset_path, split)
      # Parcurgem fiecare subfolder din acel split (ex dry, oily, acne)
    for category in os.listdir(split_path):
        category_path = os.path.join(split_path, category)
        if os.path.isdir(category_path):
            count = len([
                f for f in os.listdir(category_path)
                if os.path.isfile(os.path.join(category_path, f))
            ])
            print(f"   - {category}: {count} imagini")
