import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models
from torchvision.models import ResNet18_Weights
import copy
import time


def load_breed_names(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {breed['id']: breed['name_en'] for breed in data['breeds']}


def get_data_loaders(data_dir, batch_size=32, num_workers=0):
    data_transforms = {
        'train': transforms.Compose([
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    full_dataset = datasets.ImageFolder(data_dir, transform=data_transforms['train'])
    class_names = full_dataset.classes

    val_split = 0.2
    val_size = int(len(full_dataset) * val_split)
    train_size = len(full_dataset) - val_size

    train_dataset, val_dataset = random_split(
        full_dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )

    val_dataset.dataset = copy.deepcopy(full_dataset)
    val_dataset.dataset.transform = data_transforms['val']

    dataloaders = {
        'train': DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers),
        'val': DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    }

    dataset_sizes = {'train': train_size, 'val': val_size}

    return dataloaders, dataset_sizes, class_names


def train_model(model, dataloaders, dataset_sizes, criterion, optimizer, scheduler, num_epochs=25, device='cuda'):
    since = time.time()

    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(num_epochs):
        print(f'Epoch {epoch}/{num_epochs - 1}')
        print('-' * 20)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            if phase == 'train':
                scheduler.step()

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

        print()

    time_elapsed = time.time() - since
    print(f'Training complete in {time_elapsed // 60:.0f}m {time_elapsed % 60:.0f}s')
    print(f'Best val Acc: {best_acc:.4f}')

    model.load_state_dict(best_model_wts)
    return model


def create_model(num_classes, device='cuda'):
    model = models.resnet18(weights=ResNet18_Weights.DEFAULT)

    for param in model.parameters():
        param.requires_grad = False

    num_ftrs = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_ftrs, 512),
        nn.ReLU(),
        nn.Dropout(0.3),
        nn.Linear(512, num_classes)
    )

    model = model.to(device)
    return model


def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'Using device: {device}')

    data_dir = './data'
    batch_size = 32
    num_epochs = 20
    learning_rate = 0.001

    if not os.path.exists(data_dir):
        print(f'Data directory {data_dir} not found.')
        print('Please create data directory with structure: data/breed_name/*.jpg')
        return

    os.makedirs('./models', exist_ok=True)

    dataloaders, dataset_sizes, class_names = get_data_loaders(data_dir, batch_size=batch_size)
    num_classes = len(class_names)

    print(f'Found {num_classes} classes: {class_names}')

    with open('./models/class_names.json', 'w', encoding='utf-8') as f:
        json.dump(class_names, f, ensure_ascii=False, indent=2)

    model = create_model(num_classes, device=device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)

    print('Starting training...')
    model = train_model(
        model, dataloaders, dataset_sizes,
        criterion, optimizer, scheduler,
        num_epochs=num_epochs, device=device
    )

    torch.save(model.state_dict(), './models/dog_breed_resnet18.pth')
    print('Model saved to ./models/dog_breed_resnet18.pth')

    print('Fine-tuning all layers with smaller learning rate...')
    for param in model.parameters():
        param.requires_grad = True

    optimizer = optim.SGD(model.parameters(), lr=0.0001, momentum=0.9)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)

    model = train_model(
        model, dataloaders, dataset_sizes,
        criterion, optimizer, scheduler,
        num_epochs=10, device=device
    )

    torch.save(model.state_dict(), './models/dog_breed_resnet18_finetuned.pth')
    print('Fine-tuned model saved to ./models/dog_breed_resnet18_finetuned.pth')


if __name__ == '__main__':
    main()
