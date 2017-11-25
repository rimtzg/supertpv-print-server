drop table if exists printers;
create table printers (
  id integer primary key autoincrement,
  name text not null,
  route text not null,
  chars int not null
);
create table templates (
  id integer primary key autoincrement,
  name text not null,
  url text not null,
  'text' text not null
);