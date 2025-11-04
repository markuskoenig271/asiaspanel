# global (recommended)
git config --global user.name "Markus Koenig"
git config --global user.email "markus_koenig73@yahoo.de"
git config --global --list
gh auth login

git init
gh repo create asiaspanel --public --source=. --remote=origin --push