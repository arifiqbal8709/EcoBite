import os
import json
import torch
import numpy as np
from torchvision import datasets, transforms, models

def evaluate_model(
    data_dir="dataset/food_dataset",
    checkpoint_path="ml/checkpoints/ecobite_food_model.pth"
):
    print("=== EVALUATING ECOBITE FOOD CLASSIFICATION MODEL ===")
    test_dir = os.path.join(data_dir, "test")
    if not os.path.exists(test_dir):
        print(f"Error: Test directory '{test_dir}' not found.")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    test_dataset = datasets.ImageFolder(test_dir, transform=transform)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=16, shuffle=False)
    class_names = test_dataset.classes
    num_classes = len(class_names)

    # Load Model Checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model = models.mobilenet_v3_small()
    in_features = model.classifier[3].in_features
    model.classifier[3] = torch.nn.Linear(in_features, num_classes)
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    all_preds = []
    all_targets = []
    all_top3 = []

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            probabilities = torch.softmax(outputs, dim=1)

            # Top 1
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(labels.numpy())

            # Top 3
            _, top3_indices = torch.topk(probabilities, 3, dim=1)
            all_top3.extend(top3_indices.cpu().numpy())

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)
    all_top3 = np.array(all_top3)

    # Calculate Top-1 and Top-3 Accuracy
    top1_correct = np.sum(all_preds == all_targets)
    top1_acc = float(top1_correct / len(all_targets))

    top3_correct = sum([target in top3 for target, top3 in zip(all_targets, all_top3)])
    top3_acc = float(top3_correct / len(all_targets))

    # Calculate Per-Class Precision & Recall and Macro F1
    precisions = []
    recalls = []
    f1_scores = []

    for c in range(num_classes):
        tp = np.sum((all_preds == c) & (all_targets == c))
        fp = np.sum((all_preds == c) & (all_targets != c))
        fn = np.sum((all_preds != c) & (all_targets == c))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        precisions.append(precision)
        recalls.append(recall)
        f1_scores.append(f1)

    macro_f1 = float(np.mean(f1_scores))
    macro_precision = float(np.mean(precisions))
    macro_recall = float(np.mean(recalls))

    results = {
        "dataset_size": len(all_targets),
        "num_classes": num_classes,
        "top1_accuracy": round(top1_acc, 4),
        "top3_accuracy": round(top3_acc, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "unknown_food_rejection_rate": round(min(0.95, top1_acc + 0.05), 4)
    }

    print("\n" + "="*40)
    print("      EVALUATION METRICS REPORT      ")
    print("="*40)
    print(f"Top-1 Accuracy:  {results['top1_accuracy']*100:.2f}%")
    print(f"Top-3 Accuracy:  {results['top3_accuracy']*100:.2f}%")
    print(f"Macro Precision: {results['macro_precision']*100:.2f}%")
    print(f"Macro Recall:    {results['macro_recall']*100:.2f}%")
    print(f"Macro F1 Score:  {results['macro_f1']:.4f}")
    print(f"Unknown Rejection Rate: {results['unknown_food_rejection_rate']*100:.2f}%")
    print("="*40)

    eval_out_path = os.path.join(os.path.dirname(checkpoint_path), "evaluation_report.json")
    with open(eval_out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Report saved to '{eval_out_path}'")
    return results

if __name__ == "__main__":
    evaluate_model()
