#!/bin/bash

cd ./Rscript

mkdir -p ../result/city

Rscript --verbose fact_check_kg_miner.R
