"""Init DB

Revision ID: 7860aadbc0d8
Revises: 
Create Date: 2022-11-28 20:07:35.714487

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7860aadbc0d8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('courses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('forum_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_courses_id'), 'courses', ['id'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('moodle_token', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('discussions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('course_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discussions_id'), 'discussions', ['id'], unique=False)
    op.create_table('tasks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('hyperlink', sa.String(), nullable=True),
    sa.Column('course_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_table('users_courses',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('course_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'course_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users_courses')
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
    op.drop_index(op.f('ix_discussions_id'), table_name='discussions')
    op.drop_table('discussions')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_courses_id'), table_name='courses')
    op.drop_table('courses')
    # ### end Alembic commands ###
