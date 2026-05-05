from temp_my_sql import MySQL, ROLE
from datetime import datetime, date, timedelta

if ROLE == "Gateway":
    db_name = '`fleet_gateway`'
else:
    db_name = '`fleet_server`'


def truncate_message():
    sql = (
        "TRUNCATE TABLE {0}.`mqtt_message` "
    ).format(db_name)

    dbh = MySQL()
    print(sql)
    result = dbh.execute(sql)
    print(result)
    dbh.close()

    return result

def truncate_task():
    sql = (
        "TRUNCATE TABLE {0}.`mqtt_task` "
    ).format(db_name)

    sql_log = (
        "TRUNCATE TABLE {0}.`mqtt_task_log` "
    ).format(db_name)

    dbh = MySQL()
    print(sql)
    result = dbh.execute(sql)
    log_result = dbh.execute(sql_log)
    print(result)
    print(log_result)

    dbh.close()

    return result

def truncate_app():
    cancel_foreign_sql = (
        "SET FOREIGN_KEY_CHECKS = 0 "
    )

    # sql = (
    #     "TRUNCATE TABLE {0}.`app_task_information` "
    # ).format(db_name)

    # relation_sql = (
    #     "TRUNCATE TABLE {0}.`app_items_in_the_task` "
    # ).format(db_name)

    relation_sql = (
        "TRUNCATE TABLE {0}.`mqtt_message_log` "
    ).format(db_name)

    resume_foreign_sql =(
        "SET FOREIGN_KEY_CHECKS = 1 "
    )

    dbh = MySQL()
    # print(sql)
    dbh.execute(cancel_foreign_sql)
    # result = dbh.execute(sql)
    # print(result)

    relation_result = dbh.execute(relation_sql)
    print(relation_sql)
    print(relation_result)

    dbh.execute(resume_foreign_sql)



    dbh.close()

    return relation_result


def main():
    truncate_message()
    truncate_task()
    truncate_app()



if __name__ == '__main__':
    main()