#!/bin/bash
set -euf -o pipefail
if [[ "$NODE_ENV" != "development" ]]
then
    node node_modules/webpack/bin/webpack.js --config webpack.config.prod.js
fi
