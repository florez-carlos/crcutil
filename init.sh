#!/bin/bash

color_red=$(tput setaf 1)
color_green=$(tput setaf 2)
color_yellow=$(tput setaf 3)
color_normal=$(tput sgr0)
setopt aliases


required_python_version_path_name="3.12"
required_python_version="3.12.10"

if [ $UID -eq 0 ]; then
    printf "%s\n" "${color_red}ERROR:${color_normal}Please DO NOT run this script with sudo"
    return 1
fi

cp git-hooks/commit-msg ./.git/hooks 
cp git-hooks/pre-commit ./.git/hooks

current_python_version=$(python -V | sed 's/Python //;s/+//')
if ! dpkg --compare-versions "$current_python_version" eq "$required_python_version";then
    printf "%s\n" ""
    printf "%s\n" "${color_red}ERROR${color_normal}: Current Python is $current_python_version but $required_python_version required"
    printf "%s\n" ""
    return 1
fi

python -m venv "$HOME"/venv/crcutil
# shellcheck source=/dev/null
. "$HOME"/venv/crcutil/bin/activate
if [ "$VIRTUAL_ENV" != "$HOME"/venv/crcutil ]; then
    printf "%s\n" ""
    printf "%s\n" "${color_red}ERROR${color_normal}: Attempted to set venv to: $HOME/venv/crcutil but current venv is $VIRTUAL_ENV"
    printf "%s\n" ""
    return 1
fi
pip install -r requirements.txt

export PYTHONPATH=$VIRTUAL_ENV/lib/python"$required_python_version_path_name"/site-packages/
