from argparse import ArgumentParser
from pprint import pprint

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import timedelta, datetime, date



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{user}:{password}@{host}:{port}/{db}'.format(user='score',
                                                                                                   password='Rysherat2',
                                                                                                   host='shopscore.devman.org',
                                                                                                   port='5432',
                                                                                                   db='shop',)
db = SQLAlchemy(app)

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    contact_name = db.Column(db.String(200))
    contact_phone = db.Column(db.String(100))
    contact_email = db.Column(db.String(150))
    status = db.Column(db.Enum('DRAFT', 'FULFILLMENT', 'CANCELED', 'COMPLETED', name='statuses'), nullable=False, index=True)
    created = db.Column(db.DateTime, nullable=False, index=True)
    confirmed = db.Column(db.DateTime, index=True)
    comment = db.Column(db.Text)
    price = db.Column(db.Numeric(9, 2))


def fetch_cmd_arguments():
    parser_description = 'Run flask server'
    parser = ArgumentParser(description=parser_description)
    parser.add_argument('-d', '--debug_mode',
                        help='Run in debug mode',
                        action='store_true')
    return parser.parse_args()


def fetch_orders_info():
    all_orders_per_days_query = (Order.query
                                 .filter(Order.created > date.today())
                                 .order_by(desc(Order.created)))
    completed_orders = (all_orders_per_days_query
                                  .filter(Order.confirmed != None)
                                  .all())
    current_orders_query = Order.query.filter(Order.confirmed == None)
    current_orders = (current_orders_query
                                .all())
    now_datetime = datetime.now()
    green_zone_timedelta = Order.created + timedelta(minutes=7)
    yellow_zone_timedelta = Order.created + timedelta(minutes=30)
    green_zone_orders = (current_orders_query
                         .filter(now_datetime <= green_zone_timedelta)
                         .all())
    yellow_zone_orders = (current_orders_query
                          .filter(now_datetime > green_zone_timedelta)
                          .all())
    red_zone_orders = (current_orders_query
                       .filter(now_datetime > yellow_zone_timedelta)
                       .all())
    current_status, title_msg, description_msg, css_value = (
        ('red', 'У нас проблемы!', 'Время ожидания больше 30 минут!', 'danger') if red_zone_orders
        else ('yellow', 'Есть над чем поработать!', 'Время ожидания не превышает 30 минут!', 'warning') if yellow_zone_orders
        else ('green', 'Все идёт по плану!', 'Время ожидания не превышает 7 минут!', 'success') if green_zone_orders
        else (None, 'Все обработано!', 'Необработанных заявок - нет!', 'success')
    )
    return {
        'completed_orders_amount': len(completed_orders),
        'current_orders_amount': len(current_orders),
        'green_zone_orders': green_zone_orders,
        'yellow_zone_orders': yellow_zone_orders,
        'red_zone_orders': red_zone_orders,
        'current_status': current_status,
        'title_msg': title_msg,
        'description_msg': description_msg,
        'css_value': css_value,
    }


@app.route('/')
def score():
    orders_info = fetch_orders_info()
    return render_template('score.html',
                           orders=orders_info,
                           time=datetime.now().strftime('%H:%M:%S'))


if __name__ == "__main__":
    cmd_args = fetch_cmd_arguments()
    if cmd_args.debug_mode:
        app.config['DEBUG'] = True
    app.run()
