import click
from app import create_app
from app.dto.ml_model_dto import MlModelRequestSchema
from app.services.ml_model_service import MlModelService
from marshmallow import ValidationError

app = create_app()

@click.group()
def cli():
    pass

@cli.command()
@click.argument('name')
@click.option('--desc', default='', help='Model description')
def create_model(name, desc):
    with app.app_context():
        try:
            data = MlModelRequestSchema().load({'name': name, 'description': desc})
        except ValidationError as error:
            raise click.ClickException(str(error.messages)) from error
        model, error = MlModelService().create(data)
        if error:
            raise click.ClickException(error)
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
