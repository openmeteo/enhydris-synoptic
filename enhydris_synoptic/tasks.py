from enhydris.celery import app

from .models import SynopticGroup
from .views import render_synoptic_group


@app.task
def create_static_files():
    """Create static html files for all enhydris-synoptic."""
    for sgroup in SynopticGroup.objects.all():
        render_synoptic_group(sgroup)
