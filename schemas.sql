create table if not exists printers (
  id integer primary key autoincrement,
  name text not null,
  route text not null,
  chars int not null
);
create table if not exists templates (
  id integer primary key autoincrement,
  name text not null,
  url text not null,
  'text' text not null
);