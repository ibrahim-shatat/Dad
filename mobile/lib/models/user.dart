class AppUser {
  final String id;
  final String email;
  final String fullName;
  final String role;

  AppUser({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
  });

  factory AppUser.fromJson(Map<String, dynamic> json) => AppUser(
        id: json['id'].toString(),
        email: (json['email'] ?? '') as String,
        fullName: (json['full_name'] ?? '') as String,
        role: (json['role'] ?? '') as String,
      );
}
