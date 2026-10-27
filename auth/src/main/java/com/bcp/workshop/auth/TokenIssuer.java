package com.bcp.workshop.auth;

import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.JOSEObjectType;
import com.nimbusds.jose.JWSSigner;
import com.nimbusds.jose.crypto.MACSigner;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;

@ApplicationScoped
public class TokenIssuer {
    public static final int TOKEN_LIFETIME_SECONDS = 300;

    private static final String TOKEN_ISSUER = "ISS";
    private static final String TOKEN_AUDIENCE = "CLAIM";
    private static final int MINIMUM_HS256_KEY_LENGTH_BYTES = 32;

    private final byte[] signingKey;

    @Inject
    public TokenIssuer(@ConfigProperty(name = "auth.jwt.secret") String secret) {
        this.signingKey = secret.getBytes(StandardCharsets.UTF_8);
        if (signingKey.length < MINIMUM_HS256_KEY_LENGTH_BYTES) {
            throw new IllegalArgumentException("HS256 signing key must be at least 32 bytes");
        }
    }

    public String create(String username, String role) {
        Instant now = Instant.now();
        JWTClaimsSet claims = new JWTClaimsSet.Builder()
                .issuer(TOKEN_ISSUER)
                .audience(TOKEN_AUDIENCE)
                .expirationTime(Date.from(now.plusSeconds(TOKEN_LIFETIME_SECONDS)))
                .claim("username", username)
                .claim("role", role)
                .build();
        SignedJWT token = new SignedJWT(
                new JWSHeader.Builder(JWSAlgorithm.HS256)
                        .type(JOSEObjectType.JWT)
                        .build(),
                claims
        );

        try {
            JWSSigner signer = new MACSigner(signingKey);
            token.sign(signer);
            return token.serialize();
        } catch (JOSEException error) {
            throw new IllegalStateException("Unable to issue authentication token", error);
        }
    }
}
