#!/usr/bin/env python3

from aws_cdk import core

from distillery.distillery_stack import DistilleryStack


app = core.App()
DistilleryStack(app, 'distillery')
core.Tags.of(app).add('distillery', 'distillery')

app.synth()
