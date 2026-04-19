# Kaggle Datasets Directory

Place your downloaded Kaggle CSV files here:

## Required Files

1. **delhi_traffic_features.csv** — From Delhi Traffic Travel Time Dataset
   - Download: https://www.kaggle.com/datasets/algozee/traffic-data-set

2. **delhi_traffic_target.csv** — From Delhi Traffic Travel Time Dataset
   - Download: https://www.kaggle.com/datasets/algozee/traffic-data-set

3. **Delivery_Logistics.csv** — From Delivery Logistics Dataset (India)
   - Download: https://www.kaggle.com/datasets/muhammadahmaddaar/delivery-logistics-dataset-india-multi-partner

## Folder Structure

```
JaamCTRL/
├── datasets/                    # THIS DIRECTORY
│   ├── delhi_traffic_features.csv
│   ├── delhi_traffic_target.csv
│   └── Delivery_Logistics.csv
└── ...
```

## Setup Instructions

1. Create a Kaggle account (if you don't have one): https://www.kaggle.com
2. Download the 3 CSV files using the links above
3. Extract and place them in this folder
4. Run: `python -m cold_chain.dataset_loader` to verify loading works

## Testing

```bash
cd <JaamCTRL root>
python -m cold_chain.dataset_loader
```

Expected output:
```
Testing Dataset Loader...
✓ Loaded Delivery Logistics sample
✓ Loaded Delhi Traffic sample
...
```

See `KAGGLE_DATASETS_SETUP.md` in the project root for detailed setup instructions.
