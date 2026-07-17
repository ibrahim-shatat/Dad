class EmailAccount {
  final String id;
  final String provider; // gmail | outlook
  final String emailAddress;

  EmailAccount({
    required this.id,
    required this.provider,
    required this.emailAddress,
  });

  factory EmailAccount.fromJson(Map<String, dynamic> json) => EmailAccount(
        id: json['id'].toString(),
        provider: (json['provider'] ?? '') as String,
        emailAddress: (json['email_address'] ?? '') as String,
      );
}
