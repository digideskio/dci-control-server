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

"""drop the files.content column

Revision ID: 348ba02aff54
Revises: db239f63b5df
Create Date: 2016-07-15 20:17:58.270279

"""

# revision identifiers, used by Alembic.
revision = '348ba02aff54'
down_revision = '01babf3af0b4'
branch_labels = None
depends_on = None

from alembic import op


def upgrade():
    op.drop_column('files', 'content')


def downgrade():
    pass
