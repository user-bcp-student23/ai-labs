package com.bcp.workshop.auth;

import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.crypto.MACVerifier;
import com.nimbusds.jwt.SignedJWT;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TokenIssuerTest {
    private static final String TEST_SECRET = "test-only-signing-key-with-at-least-32-bytes";

    @Test
    void createsSignedJwtWithRequiredClaimsAndFiveMinuteLifetime() throws Exception {
        Instant startedAt = Instant.now();
        String encodedToken = new TokenIssuer(TEST_SECRET).create("test-user", "STUDENT");
        SignedJWT token = SignedJWT.parse(encodedToken);
        var claims = token.getJWTClaimsSet();

        assertEquals(JWSAlgorithm.HS256, token.getHeader().getAlgorithm());
        assertTrue(token.verify(new MACVerifier(TEST_SECRET.getBytes(StandardCharsets.UTF_8))));
        assertEquals("ISS", claims.getIssuer());
        assertEquals(List.of("CLAIM"), claims.getAudience());
        assertEquals("test-user", claims.getStringClaim("username"));
        assertEquals("STUDENT", claims.getStringClaim("role"));
        assertTrue(claims.getExpirationTime().toInstant().isAfter(Instant.now()));
        assertTrue(claims.getExpirationTime().toInstant().isBefore(
                startedAt.plusSeconds(TokenIssuer.TOKEN_LIFETIME_SECONDS + 1L)
        ));
    }

    @Test
    void rejectsTamperedTokenSignature() throws Exception {
        String encodedToken = new TokenIssuer(TEST_SECRET).create("test-user", "STUDENT");
        String[] parts = encodedToken.split("\\.");
        char replacement = parts[2].charAt(0) == 'A' ? 'B' : 'A';
        parts[2] = replacement + parts[2].substring(1);
        SignedJWT tamperedToken = SignedJWT.parse(String.join(".", parts));

        assertFalse(tamperedToken.verify(new MACVerifier(TEST_SECRET.getBytes(StandardCharsets.UTF_8))));
    }

    @Test
    void rejectsSigningKeyShorterThanHs256Minimum() {
        assertThrows(IllegalArgumentException.class, () -> new TokenIssuer("short"));
    }
}
