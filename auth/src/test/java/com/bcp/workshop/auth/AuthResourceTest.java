package com.bcp.workshop.auth;

import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.Matchers.notNullValue;
import static org.hamcrest.Matchers.nullValue;

/**
 * Pruebas de caracterización de POST /auth/login para Issue #13 / H-AUTH-01.
 * Protegen el contrato observado y documentan el comportamiento actual frente
 * a entradas con sintaxis SQL antes de parametrizar la consulta en LegacyDatabase.
 */
@QuarkusTest
class AuthResourceTest {
    private static final String DB_URL = System.getenv().getOrDefault("AUTH_DB_URL", "jdbc:sqlite:./data/workshop.db");

    // Seed test-only fixture: a user whose password needs a parameterized query to match.
    @BeforeAll
    static void seedQuotePasswordUser() throws Exception {
        Files.createDirectories(Path.of("data"));
        try (Connection connection = DriverManager.getConnection(DB_URL);
             PreparedStatement createTable = connection.prepareStatement(
                     "CREATE TABLE IF NOT EXISTS legacy_users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT NOT NULL, display_name TEXT NOT NULL, role TEXT NOT NULL)")) {
            createTable.executeUpdate();
        }
        try (Connection connection = DriverManager.getConnection(DB_URL);
             PreparedStatement statement = connection.prepareStatement(
                     "INSERT OR IGNORE INTO legacy_users(username,password,display_name,role) VALUES (?,?,?,?)")) {
            statement.setString(1, "quote_user");
            statement.setString(2, "O'Reilly1!");
            statement.setString(3, "Quote User");
            statement.setString(4, "STUDENT");
            statement.executeUpdate();
        }
    }

    @Test
    void logsInWithWorkshopUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("student"))
                .body("token", notNullValue());
    }

    @Test
    void logsInWithTrainerUser() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"trainer\",\"password\":\"Trainer123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("trainer"))
                .body("user.role", is("TRAINER"));
    }

    @Test
    void rejectsIncorrectPassword() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"wrong\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("message", notNullValue())
                .body("token", nullValue());
    }

    @Test
    void rejectsUnknownUsername() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"no_such_user\",\"password\":\"whatever\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void doesNotTrimPassword() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"Workshop123! \",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401);
    }

    @Test
    void usernameComparisonIsCaseSensitive() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"Student\",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401);
    }

    @Test
    void rejectsMissingBody() {
        given()
                .contentType("application/json")
                .when().post("/auth/login")
                .then()
                .statusCode(400);
    }

    @Test
    void rejectsBlankUsername() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"   \",\"password\":\"Workshop123!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", notNullValue());
    }

    @Test
    void rejectsBlankPassword() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"   \",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(400)
                .body("message", notNullValue());
    }

    @Test
    void sqlSyntaxInUsernameDoesNotAuthenticate() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"' OR '1'='1\",\"password\":\"whatever\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void sqlSyntaxInPasswordDoesNotAuthenticate() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student\",\"password\":\"' OR '1'='1\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void sqlCommentInUsernameDoesNotSkipPasswordCheck() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"student' --\",\"password\":\"wrong\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401)
                .body("token", nullValue());
    }

    @Test
    void unclosedQuoteDoesNotCauseInternalError() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"o'hara\",\"password\":\"whatever\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(401);
    }

    @Test
    void legitimatePasswordWithQuoteIsComparedAsText() {
        given()
                .contentType("application/json")
                .body("{\"username\":\"quote_user\",\"password\":\"O'Reilly1!\",\"client\":\"angular-workshop\"}")
                .when().post("/auth/login")
                .then()
                .statusCode(200)
                .body("user.username", is("quote_user"));
    }
}
