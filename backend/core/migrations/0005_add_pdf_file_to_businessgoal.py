# Generated manually to fix missing pdf_file field

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_fix_recommendation_constraint'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessgoal',
            name='pdf_file',
            field=models.FileField(
                blank=True, 
                help_text='Optional PDF document with additional goal details', 
                null=True, 
                upload_to='business_goals/pdfs/', 
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])]
            ),
        ),
    ] 