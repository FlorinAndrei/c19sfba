#!/usr/bin/env bash

rm -f time_series_covid19_confirmed_US.csv
python3.7 c19sfba.py || exit

# Run these commands once to cache git credentials in Linux.
#git config --global credential.helper store
#git config --global user.email your@email.com
#git config --global user.name yourUserName
#git add *; git commit -m "rebuild"; git push
# Enter the password once.
# After this, git will not ask for credentials again.

# Nuke all git history
# make orphan branch
git checkout --orphan rebuild
# If you have .gitignore, then "git add *" never exits cleanly.
git add * || true
git commit -m "rebuild"
# delete master
git branch -D master
# rename new branch
git branch -m master
git push -f origin master
