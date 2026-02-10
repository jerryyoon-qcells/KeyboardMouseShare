using System;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;

namespace KeyboardMouseShare.Auth
{
    /// <summary>
    /// Manages passphrase generation, validation, and storage
    /// Provides secure hashing for authentication between devices
    /// </summary>
    public interface IPassphraseManager
    {
        /// <summary>Generate a random 6-character alphanumeric passphrase</summary>
        string GeneratePassphrase();
        
        /// <summary>Validate passphrase format (6 chars, alphanumeric)</summary>
        (bool IsValid, string? Error) ValidatePassphrase(string? passphrase);
        
        /// <summary>Hash passphrase for secure storage/comparison</summary>
        string HashPassphrase(string passphrase);
        
        /// <summary>Verify passphrase against stored hash</summary>
        bool VerifyPassphrase(string passphrase, string hash);
    }

    /// <summary>
    /// Passphrase manager implementation
    /// Uses PBKDF2 for secure hashing
    /// </summary>
    public class PassphraseManager : IPassphraseManager
    {
        private const int MinLength = 6;
        private const int MaxLength = 16;
        private const string ValidChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        private readonly ILogger<PassphraseManager> _logger;

        // PBKDF2 parameters
        private const int IterationCount = 10000;
        private const int HashSize = 32; // 256 bits
        private const int SaltSize = 16; // 128 bits

        public PassphraseManager(ILogger<PassphraseManager> logger)
        {
            _logger = logger;
        }

        /// <summary>
        /// Generate random 6-character alphanumeric passphrase
        /// </summary>
        public string GeneratePassphrase()
        {
            var sb = new StringBuilder();
            using (var rng = RandomNumberGenerator.Create())
            {
                var buffer = new byte[6];
                rng.GetBytes(buffer);

                foreach (var b in buffer)
                {
                    sb.Append(ValidChars[b % ValidChars.Length]);
                }
            }

            var passphrase = sb.ToString();
            _logger.LogInformation("Generated new passphrase: {Passphrase}",
                MaskPassphrase(passphrase));
            return passphrase;
        }

        /// <summary>
        /// Validate passphrase format
        /// </summary>
        public (bool IsValid, string? Error) ValidatePassphrase(string? passphrase)
        {
            if (string.IsNullOrEmpty(passphrase))
                return (false, "Passphrase cannot be empty");

            if (passphrase.Length < MinLength)
                return (false, $"Passphrase must be at least {MinLength} characters");

            if (passphrase.Length > MaxLength)
                return (false, $"Passphrase cannot exceed {MaxLength} characters");

            // Must be alphanumeric (letters and numbers only)
            if (!Regex.IsMatch(passphrase, "^[A-Za-z0-9]+$"))
                return (false, "Passphrase must be alphanumeric (letters and numbers only)");

            return (true, null);
        }

        /// <summary>
        /// Hash passphrase using PBKDF2
        /// Returns format: iteration$salt$hash
        /// </summary>
        public string HashPassphrase(string passphrase)
        {
            var (isValid, error) = ValidatePassphrase(passphrase);
            if (!isValid)
                throw new ArgumentException(error ?? "Invalid passphrase");

            try
            {
                // Generate random salt
                using (var rng = RandomNumberGenerator.Create())
                {
                    var salt = new byte[SaltSize];
                    rng.GetBytes(salt);

                    // Hash with PBKDF2
                    using (var pbkdf2 = new Rfc2898DeriveBytes(
                        passphrase,
                        salt,
                        IterationCount,
                        HashAlgorithmName.SHA256))
                    {
                        var hash = pbkdf2.GetBytes(HashSize);

                        // Format: iteration$saltBase64$hashBase64
                        var saltB64 = Convert.ToBase64String(salt);
                        var hashB64 = Convert.ToBase64String(hash);

                        var result = $"{IterationCount}${saltB64}${hashB64}";
                        
                        _logger.LogDebug("Passphrase hashed successfully");
                        return result;
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to hash passphrase");
                throw;
            }
        }

        /// <summary>
        /// Verify passphrase against stored hash
        /// </summary>
        public bool VerifyPassphrase(string passphrase, string hash)
        {
            try
            {
                var (isValid, error) = ValidatePassphrase(passphrase);
                if (!isValid)
                {
                    _logger.LogWarning("Passphrase validation failed: {Error}", error);
                    return false;
                }

                // Parse hash format: iteration$saltBase64$hashBase64
                var parts = hash.Split('$');
                if (parts.Length != 3)
                {
                    _logger.LogWarning("Invalid hash format");
                    return false;
                }

                if (!int.TryParse(parts[0], out var iterations))
                {
                    _logger.LogWarning("Invalid iteration count in hash");
                    return false;
                }

                try
                {
                    var salt = Convert.FromBase64String(parts[1]);
                    var storedHash = Convert.FromBase64String(parts[2]);

                    // Recompute hash with same salt and iterations
                    using (var pbkdf2 = new Rfc2898DeriveBytes(
                        passphrase,
                        salt,
                        iterations,
                        HashAlgorithmName.SHA256))
                    {
                        var computedHash = pbkdf2.GetBytes(HashSize);

                        // Compare hashes using constant-time comparison
                        // to prevent timing attacks
                        return ConstantTimeEquals(computedHash, storedHash);
                    }
                }
                catch (FormatException ex)
                {
                    _logger.LogWarning(ex, "Failed to parse hash format");
                    return false;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during passphrase verification");
                return false;
            }
        }

        /// <summary>
        /// Constant-time byte array comparison (prevents timing attacks)
        /// </summary>
        private static bool ConstantTimeEquals(byte[] a, byte[] b)
        {
            if (a.Length != b.Length)
                return false;

            int result = 0;
            for (int i = 0; i < a.Length; i++)
            {
                result |= a[i] ^ b[i];
            }

            return result == 0;
        }

        /// <summary>
        /// Mask passphrase for logging (show only first and last char)
        /// </summary>
        private static string MaskPassphrase(string passphrase)
        {
            if (passphrase.Length <= 2)
                return "***";

            return $"{passphrase[0]}****{passphrase[^1]}";
        }
    }

    /// <summary>
    /// Validates application configuration parameters
    /// </summary>
    public interface IConfigValidator
    {
        /// <summary>Validate device name format</summary>
        (bool IsValid, string? Error) ValidateDeviceName(string? name);
        
        /// <summary>Validate IP address format</summary>
        (bool IsValid, string? Error) ValidateIpAddress(string? ip);
        
        /// <summary>Validate port number</summary>
        (bool IsValid, string? Error) ValidatePort(int port);
        
        /// <summary>Validate log level</summary>
        (bool IsValid, string? Error) ValidateLogLevel(string? logLevel);
    }

    /// <summary>
    /// Configuration validator implementation
    /// </summary>
    public class ConfigValidator : IConfigValidator
    {
        private readonly ILogger<ConfigValidator> _logger;

        public ConfigValidator(ILogger<ConfigValidator> logger)
        {
            _logger = logger;
        }

        /// <summary>Device name: 1-64 chars, alphanumeric + spaces/hyphens</summary>
        public (bool IsValid, string? Error) ValidateDeviceName(string? name)
        {
            if (string.IsNullOrEmpty(name))
                return (false, "Device name cannot be empty");

            if (name.Length > 64)
                return (false, "Device name cannot exceed 64 characters");

            if (!Regex.IsMatch(name, @"^[A-Za-z0-9 -]+$"))
                return (false, "Device name must contain only alphanumeric characters, spaces, and hyphens");

            return (true, null);
        }

        /// <summary>IP address: valid IPv4 or IPv6</summary>
        public (bool IsValid, string? Error) ValidateIpAddress(string? ip)
        {
            if (string.IsNullOrEmpty(ip))
                return (false, "IP address cannot be empty");

            if (System.Net.IPAddress.TryParse(ip, out _))
                return (true, null);

            return (false, "Invalid IP address format");
        }

        /// <summary>Port: 1024-65535 (non-privileged ports)</summary>
        public (bool IsValid, string? Error) ValidatePort(int port)
        {
            if (port < 1024)
                return (false, "Port must be at least 1024 (non-privileged)");

            if (port > 65535)
                return (false, "Port must be at most 65535");

            return (true, null);
        }

        /// <summary>Log level: Trace, Debug, Information, Warning, Error, Critical</summary>
        public (bool IsValid, string? Error) ValidateLogLevel(string? logLevel)
        {
            if (string.IsNullOrEmpty(logLevel))
                return (true, null); // Optional, defaults to Information

            var validLevels = new[] 
            { 
                "Trace", "Debug", "Information", "Warning", "Error", "Critical" 
            };

            if (!validLevels.Contains(logLevel, StringComparer.OrdinalIgnoreCase))
                return (false, $"Invalid log level. Must be one of: {string.Join(", ", validLevels)}");

            return (true, null);
        }
    }
}
