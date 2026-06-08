import os
import argparse
import numpy as np
import cv2
from pathlib import Path


def load_dataset(dataset_dir, img_size=(224, 224)):
    images = []
    labels = []

    with_mask_dir = os.path.join(dataset_dir, "with_mask")
    without_mask_dir = os.path.join(dataset_dir, "without_mask")

    for label_val, (dir_path, label_name) in enumerate(
        [(with_mask_dir, "with_mask"), (without_mask_dir, "without_mask")]
    ):
        if not os.path.isdir(dir_path):
            print(f"[WARN] Directory not found: {dir_path}")
            continue

        count = 0
        for fname in os.listdir(dir_path):
            fpath = os.path.join(dir_path, fname)
            try:
                img = cv2.imread(fpath)
                if img is None:
                    continue
                img = cv2.resize(img, img_size)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                images.append(img)
                labels.append(label_val)
                count += 1
            except Exception:
                continue
        print(f"  {label_name}: {count} images loaded")

    return np.array(images, dtype=np.float32), np.array(labels, dtype=np.int32)


def build_model(img_size=(224, 224)):
    from tensorflow.keras import layers, models
    from tensorflow.keras.applications import MobileNetV2

    base = MobileNetV2(
        input_shape=(*img_size, 3), include_top=False, weights="imagenet"
    )
    base.trainable = False

    model = models.Sequential(
        [
            base,
            layers.GlobalAveragePooling2D(),
            layers.Dropout(0.3),
            layers.Dense(128, activation="relu"),
            layers.Dropout(0.2),
            layers.Dense(1, activation="sigmoid"),
        ]
    )

    model.compile(
        optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"]
    )
    return model, base


def train(args):
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping

    print("=" * 50)
    print("  Mask Classifier Training")
    print("=" * 50)

    dataset_dir = args.dataset
    if not os.path.isdir(dataset_dir):
        print(f"ERROR: Dataset directory not found: {dataset_dir}")
        print("Expected structure:")
        print(f"  {dataset_dir}/with_mask/   (images of faces with mask)")
        print(f"  {dataset_dir}/without_mask/ (images of faces without mask)")
        return

    print(f"\nLoading dataset from: {dataset_dir}")
    images, labels = load_dataset(dataset_dir, img_size=(args.img_size, args.img_size))

    if len(images) == 0:
        print("ERROR: No images found in dataset directory")
        return

    images = images / 255.0

    mask_count = np.sum(labels == 1)
    no_mask_count = np.sum(labels == 0)
    print(f"\nDataset: {len(images)} total, {mask_count} with_mask, {no_mask_count} without_mask")

    datagen = ImageDataGenerator(
        rotation_range=20,
        width_shift_range=0.15,
        height_shift_range=0.15,
        horizontal_flip=True,
        zoom_range=0.15,
        shear_range=0.1,
        fill_mode="nearest",
        validation_split=0.2,
    )

    train_gen = datagen.flow(images, labels, batch_size=args.batch_size, subset="training")
    val_gen = datagen.flow(images, labels, batch_size=args.batch_size, subset="validation")

    print("\nBuilding model (MobileNetV2 transfer learning)...")
    model, base = build_model(img_size=(args.img_size, args.img_size))
    model.summary()

    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "mask_model.h5")

    callbacks = [
        ModelCheckpoint(
            model_path, monitor="val_accuracy", save_best_only=True, mode="max", verbose=1
        ),
        EarlyStopping(
            monitor="val_loss", patience=5, restore_best_weights=True, verbose=1
        ),
    ]

    print(f"\nPhase 1: Training classification head ({args.epochs_phase1} epochs)...")
    history1 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=args.epochs_phase1,
        callbacks=callbacks,
    )

    print(f"\nPhase 2: Fine-tuning ({args.epochs_phase2} epochs)...")
    base.trainable = True
    for layer in base.layers[:-20]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(1e-5),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )

    history2 = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=args.epochs_phase1 + args.epochs_phase2,
        initial_epoch=args.epochs_phase1,
        callbacks=callbacks,
    )

    print(f"\nModel saved to: {model_path}")
    print("Training complete!")


if __name__ == "__main__":
    import tensorflow as tf

    parser = argparse.ArgumentParser(description="Train mask classifier model")
    parser.add_argument(
        "--dataset",
        type=str,
        default="./dataset",
        help="Path to dataset directory (with_mask/ and without_mask/ subdirs)",
    )
    parser.add_argument("--img-size", type=int, default=224, help="Input image size")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--epochs-phase1", type=int, default=10, help="Epochs for head training")
    parser.add_argument("--epochs-phase2", type=int, default=10, help="Epochs for fine-tuning")
    args = parser.parse_args()

    train(args)
