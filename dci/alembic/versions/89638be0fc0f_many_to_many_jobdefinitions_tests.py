#
# Copyright (C) 2016 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Many to many jobdefinitions tests

Revision ID: 89638be0fc0f
Revises: caea3df243f3
Create Date: 2016-04-19 16:39:03.964316

"""

# revision identifiers, used by Alembic.
revision = '89638be0fc0f'
down_revision = 'caea3df243f3'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('jobdefinitions', 'test_id')

    op.create_table(
        'jobdefinition_tests',
        sa.Column('jobdefinition_id', sa.String(36),
                  sa.ForeignKey('jobdefinitions.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
        sa.Column('test_id', sa.String(36),
                  sa.ForeignKey('tests.id', ondelete="CASCADE"),
                  nullable=False, primary_key=True),
    )


def downgrade():
    """Not supported at this time, will be implemented later"""
    pass
