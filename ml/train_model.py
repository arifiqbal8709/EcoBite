import os
import json
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models

def train_food_classifier(
    data_dir="dataset/food_dataset",
    checkpoint_dir="ml/checkpoints",
    epochs=10,
    batch_size=16,
    learning_rate=0.001
):
    print("=== STARTING ECOBITE PYTORCH MODEL TRAINING ===")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using compute device: {device}")

    os.makedirs(checkpoint_dir, exist_ok=True)

    # Data augmentations and normalizations
    data_transforms = {
        "train": transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        "val": transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
    }

    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")

    image_datasets = {
        "train": datasets.ImageFolder(train_dir, data_transforms["train"]),
        "val": datasets.ImageFolder(val_dir, data_transforms["val"])
    }

    dataloaders = {
        "train": torch.utils.data.DataLoader(image_datasets["train"], batch_size=batch_size, shuffle=True, num_workers=0),
        "val": torch.utils.data.DataLoader(image_datasets["val"], batch_size=batch_size, shuffle=False, num_workers=0)
    }

    class_names = image_datasets["train"].classes
    num_classes = len(class_names)
    print(f"Loaded dataset with {num_classes} classes: {class_names[:5]}...")

    # Load MobileNetV3 Pretrained Backbone
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
    
    # Replace final classifier layer
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=2, factor=0.5)

    best_acc = 0.0
    checkpoint_path = os.path.join(checkpoint_dir, "ecobite_food_model.pth")
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}

    start_time = time.time()

    for epoch in range(epochs):
        print(f"\nEpoch {epoch+1}/{epochs}")
        print("-" * 30)

        for phase in ["train", "val"]:
            if phase == "train":
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == "train"):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == "train":
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / len(image_datasets[phase])
            epoch_acc = running_corrects.double() / len(image_datasets[phase])

            print(f"{phase.capitalize()} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}")

            if phase == "train":
                history["train_loss"].append(epoch_loss)
                history["train_acc"].append(epoch_acc.item())
            else:
                history["val_loss"].append(epoch_loss)
                history["val_acc"].append(epoch_acc.item())
                scheduler.step(epoch_loss)

                if epoch_acc > best_acc:
                    best_acc = epoch_acc
                    torch.save({
                        "epoch": epoch + 1,
                        "model_state_dict": model.state_dict(),
                        "optimizer_state_dict": optimizer.state_dict(),
                        "best_acc": best_acc.item(),
                        "class_names": class_names
                    }, checkpoint_path)
                    print(f"Saved Checkpoint: Best Val Acc = {best_acc:.4f} at {checkpoint_path}")

    elapsed = time.time() - start_time
    print(f"\nTraining Complete in {elapsed//60:.0f}m {elapsed%60:.0f}s. Best Val Accuracy: {best_acc:.4f}")
    
    meta_path = os.path.join(checkpoint_dir, "model_metadata.json")
    with open(meta_path, "w") as f:
        json.dump({
            "model_architecture": "mobilenet_v3_small",
            "num_classes": num_classes,
            "class_names": class_names,
            "best_val_accuracy": float(best_acc),
            "epochs_trained": epochs,
            "training_time_sec": round(elapsed, 2)
        }, f, indent=2)

if __name__ == "__main__":
    train_food_classifier(epochs=5)
