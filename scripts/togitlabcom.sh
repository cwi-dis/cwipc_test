#!/bin/bash
case x$1 in
x)
	echo usage: $0 newurl
	echo Shows current remotes for this repo. You are prompted to say whether you want
	echo to cange origin to vo-gitlab and add newurl as the new origin
	exit 0
	;;
esac
git remote -v
echo "Do you want to change origin to vo-gitlab and add a new origin $1 ? Type YES if so - "
read answer
if [ x$answer == xYES ]; then
	set -xe
	git remote rename origin vo-gitlab
	git fetch
	git remote add origin $1
	git fetch origin
	git checkout master
	git branch --set-upstream-to origin/master
	git pull
	git remote -v
	git branch -a
else
	exit 1
fi
