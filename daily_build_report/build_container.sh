#!/bin/bash


echo 'Building container...'
export HTTP_PROXY=http://proxyuser:proxypass@proxycachest.hewitt.com:3228
export HTTPS_PROXY=http://proxyuser:proxypass@proxycachest.hewitt.com:3228

docker build . -t repo-data-collection

echo 'Collection built'