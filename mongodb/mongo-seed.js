// seed.js
db = db.getSiblingDB('harvest');
if (db.getUser("harvest-api") == null) {
    db.createUser(
      {
        user: "harvest-api",
        pwd: "default-harvest-password",
        roles: [ { role: "readWrite", db: "harvest" } ]
      }
    );
}

db = db.getSiblingDB('admin');
    if (db.getUser("admin") == null) {
    db.createUser(
      {
        user: "admin",
        pwd: "default-harvest-password",
        roles: [ { role: "root", db: "admin" } ]
      }
    );
}