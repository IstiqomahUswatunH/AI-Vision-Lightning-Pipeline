from typing import Optional, Tuple, Union

import deeplake
from pytorch_lightning import LightningDataModule
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from src.data.components.deeplake_parser import DeepLakeDataset


class BreastCancerDataModule(LightningDataModule):
    """
    BreastCancerDataModule: A PyTorch Lightning Data Module for Breast Cancer Image Classification.

    This data module is designed to facilitate the preparation and loading of data for training, validation, and testing of a Breast Cancer Image Classification model. It supports loading data from both local directories (provided as strings) and deeplake datasets.

    Attributes:
        train_dir (Union[str, deeplake.dataset]): The directory path or deeplake dataset for the training data.
        val_dir (Union[str, deeplake.dataset]): The directory path or deeplake dataset for the validation data.
        test_dir (Union[str, deeplake.dataset]): The directory path or deeplake dataset for the test data.
        input_size (Tuple[int, int]): The input image size as a tuple of (height, width). Defaults to (600, 500).
        batch_size (int): The batch size for data loaders. Defaults to 64.
        num_workers (int): The number of workers for data loading. Defaults to 0.
        pin_memory (bool): Whether to pin memory during data loading. Defaults to False.

    Methods:
        num_classes(): Get the number of classes, which is 3 for Breast Cancer classification.
        setup(stage: Optional[str] = None): Load the data for the specified stage (train, validation, test, or predict).
        train_dataloader(): Get a DataLoader for the training data.
        val_dataloader(): Get a DataLoader for the validation data.
        test_dataloader(): Get a DataLoader for the test data.

    Note:
        This data module assumes that the dataset loader 'DeepLakeDataset' is available, and that it is compatible with both local directory paths and deeplake datasets.
    """

    def __init__(
        self,
        train_dir: Union[str, deeplake.dataset],  # allow for both str and deeplake.dataset
        val_dir: Union[str, deeplake.dataset],
        test_dir: Union[str, deeplake.dataset],
        input_size: Tuple[int, int] = [600, 500],
        batch_size: int = 64,
        num_workers: int = 0,
        pin_memory: bool = False,
    ):
        super().__init__()

        self.save_hyperparameters(logger=False)

        self.train_transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize((256, 256)),
            transforms.RandomRotation(20),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0], std=[1])
        ])

        self.val_transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0], std=[1])
        ])

        self.test_transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0], std=[1])
        ])

        self.ds_train = train_dir
        self.ds_val = val_dir
        self.ds_test = test_dir

        # init storage to save data

        self.data_train: Optional[Dataset] = None
        self.data_val: Optional[Dataset] = None
        self.data_test: Optional[Dataset] = None

    @property
    def num_clasess(self):
        return 3

    def setup(self, stage: Optional[str] = None):
        if stage in ['train', 'fit', None] and self.data_train is None:
            self.data_train = DeepLakeDataset(
                data_dir=self.ds_train,
                transform=self.train_transform
            )
            if len(self.data_train) == 0:
                raise ValueError('Train dataset is empty.')

        if stage in ['validation', 'fit', None]:
            if self.data_val is None:
                self.data_val = DeepLakeDataset(
                    data_dir=self.ds_val,
                    transform=self.val_transform
                )
                if len(self.data_val) == 0:
                    raise ValueError('Validation dataset is empty.')
            if self.data_test is None:
                self.data_test = DeepLakeDataset(
                    data_dir=self.ds_test,
                    transform=self.test_transform
                )
                if len(self.data_test) == 0:
                    raise ValueError('Test dataset is empty.')

        if stage == 'predict':
            if self.data_test is None:
                self.data_predict = DeepLakeDataset(
                    data_dir=self.ds_test,
                    transform=self.test_transform
                )
                if len(self.data_predict) == 0:
                    raise ValueError('Predict dataset is empty.')

    def train_dataloader(self):
        """Get a DataLoader for the training data.

        Returns:
            DataLoader: A PyTorch DataLoader configured for training data.
        """
        return DataLoader(
            dataset=self.data_train,
            batch_size=self.hparams.batch_size,
            num_workers=self.hparams.num_workers,
            pin_memory=self.hparams.pin_memory,
            shuffle=True,
        )

    def val_dataloader(self):
        """Get a DataLoader for the validation data.

        Returns:
            DataLoader: A PyTorch DataLoader configured for validation data.
        """
        return DataLoader(
            dataset=self.data_val,
            batch_size=self.hparams.batch_size,
            num_workers=self.hparams.num_workers,
            pin_memory=self.hparams.pin_memory,
            shuffle=False,
        )

    def test_dataloader(self):
        """Get a DataLoader for the test data.

        Returns:
            DataLoader: A PyTorch DataLoader configured for test data.
        """
        return DataLoader(
            dataset=self.data_test,
            batch_size=self.hparams.batch_size,
            num_workers=self.hparams.num_workers,
            pin_memory=self.hparams.pin_memory,
            shuffle=False,
        )
