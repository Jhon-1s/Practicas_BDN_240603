select * from tb_logs

select user, host from mysql.user where host='%' and account_locked='N';

select user, host from mysql.user where host='%' and account_locked='Y';