#!/usr/bin/env python

from fabric.api import local
import argparse
import sys

def check(args):
	if args.components == None:
		# find all the args here
		pass
	pass

def add(args):
	print args
	print args.component
	component = args.component
	origin = ''
	if hasattr(ns, 'origin'):
		origin = ns.origin
	else:
		raise ValueError("No origin given - defaults not yet supported")

	branch = ''
	if hasattr(ns, 'branch'):
		branch = ns.branch
	else:
		print "No branch specified - assuming master"
		branch = 'master'

	location = ''
	if hasattr(ns, 'location'):
		location = ns.location
	else:
		print "No location specified - assuming the same as component name"
		location = component


	# add the remote
	local('git remote add -f %s %s' % (args.component, args.origin))
	print 'git remote add -f %s %s' % (args.component, args.origin)

	# no-commit merge - pull it in and wait
	local('git merge -s ours --squash --no-commit %s/%s' % (component, branch))
	print('git merge -s ours --squash --no-commit %s/%s' % (component, branch))

	# read the tree to the required location
	local('git read-tree --prefix=%s -u %s/%s' % (location, component, branch))
	print('git read-tree --prefix=%s/ -u %s/%s' % (location, component, branch))

	# make the addition to the .gitignore
	with open('%s/.gitignore' % (location,), 'a') as gitignore:
		gitignore.write("\n.gee_component\n")

	# create the component file
	with open('%s/.gee_component' % (location,), 'w') as comp_file:
		comp_file.write("\n")

	# add the .gitignore file to the commit
	local('git add %s/.gitignore' % (location,))
	print('git add %s/.gitignore' % (location,))
	
	# commit
	local('git commit -m "[gee] Added component %s to project at location %s"' %(component, location))
	print('git commit -m "[gee] Added component %s to project at location %s"' %(component, location))
	


parser = argparse.ArgumentParser(
				description="Tool for working with component-based architectures in Git"
				)
subparsers = parser.add_subparsers()

add_parser = subparsers.add_parser("add", help="Add a component to the repo")
add_parser.add_argument("component", action="store")
add_parser.add_argument("--origin", "-o", action="store")
add_parser.set_defaults(func=add)


check_parser = subparsers.add_parser("check", help="Check component status")
check_parser.add_argument("components", action="store", nargs='*')
check_parser.set_defaults(func=check)

ns = parser.parse_args()
ns.func(ns)
