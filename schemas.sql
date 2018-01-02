create table if not exists ticket_printers (
  id integer primary key autoincrement,
  name text not null,
  route text not null,
  chars int not null,
  uri text not null
);
create table if not exists label_printers (
  id integer primary key autoincrement,
  name text not null,
  queue text not null,
  width int not null,
  height int not null,
  gap int not null,
  direct_thermal text not null,
  uri text not null
);
create table if not exists templates (
  id integer primary key autoincrement,
  name text not null,
  url text not null unique,
  'text' text not null
);