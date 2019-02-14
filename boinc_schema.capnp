# boinc_schema.capnp

struct User {
  id @0 :UInt32;
  total_credit @1 :Float64;
  expavg_credit @2 :Float64;
  cpid @3 :Text;
}

struct Users {
  user @0 :List(User);
}
