"""Update models safely

Revision ID: ea4786cd1c82
Revises: 9bf3f13096c2
Create Date: 2025-05-13 18:15:06.835872
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ea4786cd1c82'
down_revision = '9bf3f13096c2'
branch_labels = None
depends_on = None


def upgrade():
    # DO NOT DROP TABLES (safe migration)
    # op.drop_table('estudent')
    # op.drop_table('student')

    with op.batch_alter_table('attendance', schema=None) as batch_op:
        batch_op.drop_constraint('attendance_student_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'e_students', ['student_id'], ['id'])

    with op.batch_alter_table('e_students') as batch_op:
        batch_op.execute("ALTER TABLE e_students ALTER COLUMN class_id TYPE INTEGER USING class_id::integer")



def downgrade():
    with op.batch_alter_table('e_students', schema=None) as batch_op:
    # Use an explicit cast with "USING"
        batch_op.alter_column(
            'class_id',
            existing_type=sa.VARCHAR(length=10),
            type_=sa.Integer(),
            existing_nullable=False,
            postgresql_using='class_id::integer'  # 👈 Add this
        )
        batch_op.create_foreign_key(None, 'class', ['class_id'], ['id'])


    # COMMENTED OUT – prevent unsafe restoration unless intentional
    # op.create_table('student', ...)
    # op.create_table('estudent', ...)


    # op.create_table('student',
    # sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('student_id_seq'::regclass)"), autoincrement=True, nullable=False),
    # sa.Column('teacher_id', sa.INTEGER(), autoincrement=False, nullable=True),
    # sa.Column('student_name', sa.VARCHAR(length=256), autoincrement=False, nullable=True),
    # sa.Column('father_name', sa.VARCHAR(length=256), autoincrement=False, nullable=True),
    # sa.Column('mother_name', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    # sa.Column('mobile_number', sa.VARCHAR(length=15), autoincrement=False, nullable=True),
    # sa.Column('student_class', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    # sa.Column('village', sa.VARCHAR(length=256), autoincrement=False, nullable=True),
    # sa.Column('previous_school', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    # sa.Column('remarks', sa.VARCHAR(length=512), autoincrement=False, nullable=True),
    # sa.Column('is_admitted', sa.BOOLEAN(), autoincrement=False, nullable=True),
    # sa.Column('admission_date', sa.DATE(), autoincrement=False, nullable=True),
    # sa.Column('follow_up_date', sa.DATE(), autoincrement=False, nullable=True),
    # sa.ForeignKeyConstraint(['teacher_id'], ['teacher.id'], name='student_teacher_id_fkey'),
    # sa.PrimaryKeyConstraint('id', name='student_pkey'),
    # postgresql_ignore_search_path=False
    # )
    # op.create_table('estudent',
    # sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    # sa.Column('student_id', sa.INTEGER(), autoincrement=False, nullable=True),
    # sa.Column('roll_number', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    # sa.Column('class_id', sa.INTEGER(), autoincrement=False, nullable=True),
    # sa.Column('section', sa.VARCHAR(length=10), autoincrement=False, nullable=True),
    # sa.Column('status', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    # sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    # sa.ForeignKeyConstraint(['class_id'], ['class.id'], name='estudent_class_id_fkey'),
    # sa.ForeignKeyConstraint(['student_id'], ['student.id'], name='estudent_student_id_fkey'),
    # sa.PrimaryKeyConstraint('id', name='estudent_pkey'),
    # sa.UniqueConstraint('roll_number', name='estudent_roll_number_key'),
    # sa.UniqueConstraint('student_id', name='estudent_student_id_key')
    # )
    # ### end Alembic commands ###
