from aws_cdk import (
    aws_dynamodb as _dynamodb,
    aws_events as _events,
    aws_events_targets as _targets,
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_logs as _logs,
    aws_ssm as _ssm,
    core
)


class DistilleryStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = _dynamodb.Table(
            self, 'cidr',
            partition_key={'name': 'pk', 'type': _dynamodb.AttributeType.STRING},
            sort_key={'name': 'sk', 'type': _dynamodb.AttributeType.STRING},
            billing_mode=_dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute='token',
            removal_policy=core.RemovalPolicy.DESTROY
        )
        
        table.add_global_secondary_index(
            index_name='firstip',
            partition_key={'name': 'pk', 'type': _dynamodb.AttributeType.STRING},
            sort_key={'name': 'firstip', 'type': _dynamodb.AttributeType.NUMBER},
            projection_type=_dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=['created']
        )

        table.add_global_secondary_index(
            index_name='lastip',
            partition_key={'name': 'pk', 'type': _dynamodb.AttributeType.STRING},
            sort_key={'name': 'lastip', 'type': _dynamodb.AttributeType.NUMBER},
            projection_type=_dynamodb.ProjectionType.INCLUDE,
            non_key_attributes=['created']
        )
        
        db_param = _ssm.StringParameter(
            self, 'db_param',
            description='distillery-tablename',
            parameter_name='/distillery/tablename',
            string_value=table.table_name,
            tier=_ssm.ParameterTier.STANDARD,
        )
        
        dl_tracker = _ssm.StringParameter(
            self, 'dl_tracker',
            description='distillery-tracker',
            parameter_name='/distillery/tracker',
            string_value='empty',
            tier=_ssm.ParameterTier.STANDARD,
        )

        layer = _lambda.LayerVersion(
            self, 'requests_layer',
            code=_lambda.Code.asset('layer'),
            license='Apache License 2.0',
            description='Requests is an elegant and simple HTTP library for Python, built for human beings.'
        )

        amazon_role = _iam.Role(self, 'amazon_role', assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com'))
        amazon_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'))
        amazon_role.add_to_policy(_iam.PolicyStatement(actions=['ssm:PutParameter','ssm:GetParameter','dynamodb:PutItem'],resources=['*']))

        amazon_lambda = _lambda.Function(
            self, 'amazon_lambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset('amazon'),
            handler='download.handler',
            role=amazon_role,
            timeout=core.Duration.seconds(900),
            environment=dict(
                DYNAMODB_TABLE=table.table_name,
                SSM_PARAMETER='/distillery/tracker'
            ),
            layers=[layer]
        )

        amazon_logs = _logs.LogGroup(
            self, 'amazon_logs',
            log_group_name='/aws/lambda/'+amazon_lambda.function_name,
            retention=_logs.RetentionDays.ONE_DAY,
            removal_policy=core.RemovalPolicy.DESTROY
        )

        search_role = _iam.Role(self, 'search_role', assumed_by=_iam.ServicePrincipal('lambda.amazonaws.com'))
        search_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'))
        search_role.add_to_policy(_iam.PolicyStatement(actions=['dynamodb:Query'],resources=['*']))

        search_lambda = _lambda.Function(
            self, 'search_lambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.asset('search'),
            handler='search.handler',
            role=search_role,
            timeout=core.Duration.seconds(30),
            environment=dict(
                DYNAMODB_TABLE=table.table_name,
            )
        )

        search_logs = _logs.LogGroup(
            self, 'search_logs',
            log_group_name='/aws/lambda/'+search_lambda.function_name,
            retention=_logs.RetentionDays.ONE_DAY,
            removal_policy=core.RemovalPolicy.DESTROY
        )
        
        amazon_event = _events.Rule(
            self, 'amazon_event',
            schedule=_events.Schedule.cron(
                minute='0',
                hour='*',
                month='*',
                week_day='*',
                year='*'
            )
        )
        amazon_event.add_target(_targets.LambdaFunction(amazon_lambda))
