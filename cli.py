import click
import os
import json
import joblib
from app import create_app, db

app = create_app()

@click.group()
def cli():
    pass

@cli.command()
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def create_user(username, password):
    with app.app_context():
        from app.models.user import User
        if User.query.filter_by(username=username).first():
            click.echo('User already exists')
            return
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'User {username} created')

@cli.command()
@click.argument('name')
@click.option('--desc', default='', help='Model description')
def create_model(name, desc):
    with app.app_context():
        model_path = os.path.join('ml_models', f'{name}.pkl')
        if not os.path.exists(model_path):
            click.echo(f'Error: {model_path} not found')
            return

        ml = joblib.load(model_path)
        features = getattr(ml, 'feature_names_in_', None)

        from app.models.ml_model import MLModel
        if MLModel.query.filter_by(name=name).first():
            click.echo('Model already registered')
            return

        model = MLModel(
            name=name,
            description=desc,
            model_type='classifier',
            features=json.dumps(list(features)) if features is not None else '[]',
            model_path=os.path.abspath(model_path)
        )
        db.session.add(model)
        db.session.commit()
        click.echo(f'Model {name} registered')

@cli.command()
def list_models():
    with app.app_context():
        from app.models.ml_model import MLModel
        models = MLModel.query.all()
        if not models:
            click.echo('No models found')
            return
        for m in models:
            click.echo(f'{m.id}. {m.name} ({m.model_type})')

if __name__ == '__main__':
    cli()