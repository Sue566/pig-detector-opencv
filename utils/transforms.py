from torchvision import transforms


def get_train_transforms():
    return transforms.Compose([
        transforms.ToTensor(),
    ])


def get_val_transforms():
    return transforms.Compose([
        transforms.ToTensor(),
    ])
