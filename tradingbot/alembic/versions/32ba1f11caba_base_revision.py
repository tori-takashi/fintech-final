"""Base revision

Revision ID: 32ba1f11caba
Revises: 
Create Date: 2020-01-05 19:24:00.286573

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '32ba1f11caba'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('backtest_management',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('backtest_summary_id', sa.Integer(), nullable=True),
    sa.Column('timeframe', sa.Integer(), nullable=True),
    sa.Column('version', sa.String(length=100), nullable=True),
    sa.Column('close_position_on_do_nothing', sa.Boolean(), nullable=True),
    sa.Column('inverse_trading', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['backtest_summary_id'], ['backtest_summary.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('bottom_trend_follow_backtest_management')
    op.drop_table('bitmex_original_ohlcv_1min')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bitmex_original_ohlcv_1min',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('exchange_name', mysql.VARCHAR(length=100), nullable=True),
    sa.Column('asset_name', mysql.VARCHAR(length=200), nullable=True),
    sa.Column('timestamp', mysql.DATETIME(), nullable=True),
    sa.Column('open', mysql.FLOAT(), nullable=True),
    sa.Column('high', mysql.FLOAT(), nullable=True),
    sa.Column('low', mysql.FLOAT(), nullable=True),
    sa.Column('close', mysql.FLOAT(), nullable=True),
    sa.Column('volume', mysql.FLOAT(), nullable=True),
    sa.Column('ad', mysql.FLOAT(), nullable=True),
    sa.Column('atr', mysql.FLOAT(), nullable=True),
    sa.Column('obv', mysql.FLOAT(), nullable=True),
    sa.Column('roc', mysql.FLOAT(), nullable=True),
    sa.Column('rsi', mysql.FLOAT(), nullable=True),
    sa.Column('psar', mysql.FLOAT(), nullable=True),
    sa.Column('psar_trend', mysql.VARCHAR(length=10), nullable=True),
    sa.Column('slowk', mysql.FLOAT(), nullable=True),
    sa.Column('slowd', mysql.FLOAT(), nullable=True),
    sa.Column('williams_r', mysql.FLOAT(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='latin1',
    mysql_engine='InnoDB'
    )
    op.create_table('bottom_trend_follow_backtest_management',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('backtest_summary_id', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('timeframe', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('close_position_on_do_nothing', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.Column('inverse_trading', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True),
    sa.Column('bottom_trend_tick', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('middle_trend_tick', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.Column('top_trend_tick', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['backtest_summary_id'], ['backtest_summary.id'], name='fk_management_summary'),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='latin1',
    mysql_engine='InnoDB'
    )
    op.drop_table('backtest_management')
    # ### end Alembic commands ###