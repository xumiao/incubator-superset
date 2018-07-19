#!/bin/bash
#node_modules/ and dist/ will be persisted in docker volumes
#second time running these commands will be quick
cd /home/work/supernorm/superset/assets
yarn
npm run dev