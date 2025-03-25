#!/bin/env python3
import pandas as pd

# Path to your Zstandard compressed CSV file
zstd_compressed_file = 'latencies-pre-rate50000-linkveth-nodenamespace.pcap.zst.latency-flows.csv.zst'

# Read the CSV with Zstandard compression
df = pd.read_csv(zstd_compressed_file, compression='zstd')

# Show the first few rows of the dataframe
print(df.head())

print(f"Mean Latency: {df['latency'].mean()}")

print(f"STD Latency: {df['latency'].std()}")

print(f"Max Latency: {df['latency'].max()}")

df['jitter'] = df['latency'].diff().abs()

print(df.head())

print(f"Mean Jitter: {df['jitter'].mean()}")

print(f"STD Jitter: {df['jitter'].std()}")

print(f"Max Jitter: {df['jitter'].max()}")
