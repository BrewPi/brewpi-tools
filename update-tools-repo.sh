#!/bin/bash

unset CDPATH
myPath="$( cd "$( dirname "${BASH_SOURCE[0]}")" && pwd )"
cd "$myPath"

active_branch=$(git symbolic-ref -q HEAD)
active_branch=${active_branch##refs/heads/}

git fetch
changes=$(git log HEAD..origin/"$active_branch" --oneline)

if [ -z "$changes" ]; then
    # no changes
    echo "$myPath is up to date."
    exit 0
fi

read -p "$myPath is not up to date, do you want to do a git pull to update? [y/N] " yn
case "$yn" in
    y | Y | yes | YES| Yes )
        git pull;
        if [ $? -ne 0 ]; then
            echo ""
            echo "An error occurred during git pull. Please update $myPath manually."
            echo  "You can stash your local changes and then pull: cd $myPath; sudo git stash; sudo git pull"
            echo  ""
        fi
        exit 1;;
    * ) exit 0;;
esac
cd -
