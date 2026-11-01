
import getpass

from werkzeug.security import generate_password_hash
from src.database.connection import conectar


def criar_administrador():
    print("\n=== CADASTRO DO ADMINISTRADOR ===\n")

    usuario = input("Digite o usuário: ").strip()

    if not usuario:
        print("O usuário não pode ficar vazio.")
        return

    senha = getpass.getpass("Digite a senha: ")
    confirmacao = getpass.getpass("Confirme a senha: ")

    if len(senha) < 10:
        print("A senha deve possuir pelo menos 10 caracteres.")
        return

    if senha != confirmacao:
        print("As senhas não coincidem.")
        return

    conexao = conectar()

    if conexao is None:
        print("Não foi possível conectar ao banco.")
        return

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT id
            FROM administradores
            WHERE LOWER(usuario) = LOWER(%s)
            """,
            (usuario,)
        )

        if cursor.fetchone():
            print("Esse usuário já está cadastrado.")
            return

        senha_hash = generate_password_hash(
            senha,
            method="scrypt"
        )

        cursor.execute(
            """
            INSERT INTO administradores
                (usuario, senha_hash)
            VALUES (%s, %s)
            """,
            (usuario, senha_hash)
        )

        conexao.commit()

        print("\nAdministrador cadastrado com sucesso!")

    except Exception as erro:
        conexao.rollback()
        print(f"Erro ao cadastrar administrador: {erro}")

    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    criar_administrador()
