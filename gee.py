#!/usr/bin/env python

from fabric.api import local
import argparse
import sys
import json
import os.path

def check(root, args, gee):
	if not args.components:
		# Look at all the components
		args.components = gee.keys()
	for component in args.components:
		if not component in gee:
			raise ValueError("Component specified does not exist: %s" % component)
		print "Checking component %s" % component
		check_component(gee[component])

def check_component(comp):
	pass

def remove(root, args, gee):
	if not args.components:
		if not args.all:
			raise ValueError("No components specified (did you mean --all?)")
		args.components = gee.keys()
	for component in args.components:
		if not component in gee:
			raise ValueError("Component specified does not exist: %s" % component)
		print "Removing component %s" % component
		gee = remove_component(component, gee)
	# make the commit
	local('git commit -m "[gee] Removed component %s from project"' % component)
	# re-write the database
	with open('%s/.gee' % root, 'w') as comp_file:
		comp_file.write(json.dumps(gee.__dict__))

def remove_component(component, gee):
	# delete the remote
	local("git remote remove %s" % component)
	# delete the files
	local("git rm -r %s" % gee[component]["location"])
	# delete from the components database
	del gee[component]
	# return the new database
	return gee

def update(root, args, gee):
	if args.branch:
		raise ValueError("Can't specify branch when updating yet")
	if not args.components:
		if not args.all:
			raise ValueError("No components specified (did you mean --all?)")
		args.components = gee.keys()
	for component in args.components:
		if not component in gee:
			raise ValueError("Component specified does not exist: %s" % component)
		print "Updating component %s to branch %s" % (component, gee[component]["branch"])
		local("git pull -s recursive -X subtree=%s %s:%s", (gee[component]["location"], component, gee[component]["branch"]))

def add(root, args, gee):
	print args
	print args.name
	if not hasattr(args, 'origin'):
		raise ValueError("No origin given - defaults not yet supported")

	if not hasattr(args, 'branch'):
		print "No branch specified - assuming master"
		args.branch = 'master'

	if not hasattr(args, 'location'):
		print "No location specified - assuming the same as component name"
		args.location = args.name

	# add the component to the component dict
	gee[args.name] = {}
	gee[args.name]["origin"] = args.origin
	gee[args.name]["branch"] = args.branch
	gee[args.name]["location"] = args.location

	# add the remote
	local('git remote add -f %s %s' % (args.name, args.origin))
	print 'git remote add -f %s %s' % (args.name, args.origin)

	# no-commit merge - pull it in and wait
	local('git merge -s ours --squash --no-commit %s/%s' % (args.name, args.branch))
	print('git merge -s ours --squash --no-commit %s/%s' % (args.name, args.branch))

	# read the tree to the required location
	local('git read-tree --prefix=%s/ -u %s/%s' % (args.location, args.name, args.branch))
	print('git read-tree --prefix=%s/ -u %s/%s' % (args.location, args.name, args.branch))

	# make the addition to the .gitignore, if needed
	with settings(warn_only=True):
		if local('git check-ignore %s/.gee' % root).return_code:
			with open('%s/.gitignore' % root, 'a') as gitignore:
				gitignore.write("\n.gee\n")
				# add the .gitignore file to the commit
				local('git add %s/.gitignore' % root)
				print('git add %s/.gitignore' % root)
			
	# create the component file
	with open('%s/.gee' % root, 'w') as comp_file:
		comp_file.write(json.dumps(gee.__dict__))
	
	# commit
	local('git commit -m "[gee] Added component %s to project at location %s"' %(args.name, args.location))
	print('git commit -m "[gee] Added component %s to project at location %s"' %(args.name, args.location))
	


parser = argparse.ArgumentParser(
				description="Tool for working with component-based architectures in Git"
				)
subparsers = parser.add_subparsers()

add_parser = subparsers.add_parser("add", help="Add a component to the repo")
add_parser.add_argument("name", metavar="component", action="store")
add_parser.add_argument("--origin", "-o", action="store")
add_parser.add_argument("--branch", "-b", action="store")
add_parser.add_argument("--location", "-l", action="store")
add_parser.set_defaults(func=add)

check_parser = subparsers.add_parser("check", help="Check component status")
check_parser.add_argument("components", action="store", nargs='*')
check_parser.set_defaults(func=check)

remove_parser = subparsers.add_parser("remove", help="Remove a component from the repo")
remove_parser.add_argument("components", action="store", nargs="*")
remove_parser.add_argument("--all", "-a", action="store_true")
remove_parser.set_defaults(func=remove)

update_parser = subparsers.add_parser("update", help="Update a component")
update_parser.add_argument("components", action="store", nargs="*")
update_parser.add_argument("--all", "-a", action="store_true")
update_parser.add_argument("--branch", "-b", action="store")
update_parser.set_defaults(func=update)

args = parser.parse_args()

# extract git repository root
root = local("git rev-parse --show-toplevel", capture=True)

# extract gee data
gee = {}
if os.path.exists("%s/.gee" % root):
	with open('%s/.gee' % (root,), 'r') as gee_file:
		gee = json.load(gee_file)

args.func(root, args, gee)
