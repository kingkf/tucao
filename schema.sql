drop table if exists company;
create table company (
	company_id integer primary key autoincrement,
	company_name text not null
);

drop table if exists message;
create table message (
  message_id integer primary key autoincrement,
  company_id integer not null,
  text text not null,
  pub_date integer
);

drop table if exists comments;
create table comments (
	comment_id integer primary key autoincrement,
	comment_text text not null,
	message_id integer not null,
	pub_date integer
);
	
