#!/bin/bash
# bash script to remove the contents of the output folder before starting training

rm -rf /app/output/*

python train_model.py
