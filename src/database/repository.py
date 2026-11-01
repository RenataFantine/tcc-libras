

from src.database.connection import conectar


# ==================================================
# BUSCAR SINAL
# ==================================================

def buscar_sinal(nome):

    conexao = conectar()

    if conexao is None:
        return None

    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT id, nome, traducao
            FROM sinais
            WHERE LOWER(nome) = LOWER(%s)
              AND ativo = TRUE
            """,
            (nome,)
        )

        return cursor.fetchone()

    except Exception as erro:
        print(f"Erro ao buscar sinal: {erro}")
        return None

    finally:
        if cursor:
            cursor.close()
        conexao.close()


# ==================================================
# REGISTRAR RECONHECIMENTO
# ==================================================

def registrar_reconhecimento(sinal_id, confianca):

    conexao = conectar()

    if conexao is None:
        return False

    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            INSERT INTO reconhecimento (sinal_id, confianca)
            VALUES (%s, %s)
            """,
            (sinal_id, confianca)
        )

        conexao.commit()
        return True

    except Exception as erro:
        conexao.rollback()
        print(f"Erro ao registrar reconhecimento: {erro}")
        return False

    finally:
        if cursor:
            cursor.close()
        conexao.close()


# ==================================================
# REGISTRAR INÍCIO DE ACESSO
# ==================================================

def registrar_acesso_inicio():

    conexao = conectar()

    if conexao is None:
        return None

    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            INSERT INTO acessos (data_hora_inicio)
            VALUES (CURRENT_TIMESTAMP)
            RETURNING id
            """
        )

        resultado = cursor.fetchone()
        conexao.commit()

        return resultado[0] if resultado else None

    except Exception as erro:
        conexao.rollback()
        print(f"Erro ao registrar início do acesso: {erro}")
        return None

    finally:
        if cursor:
            cursor.close()
        conexao.close()


# ==================================================
# REGISTRAR FIM DE ACESSO
# ==================================================

def registrar_acesso_fim(acesso_id):

    if acesso_id is None:
        return False

    conexao = conectar()

    if conexao is None:
        return False

    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            UPDATE acessos
            SET
                data_hora_fim = CURRENT_TIMESTAMP,
                tempo_uso = GREATEST(
                    0,
                    FLOOR(
                        EXTRACT(
                            EPOCH FROM (
                                CURRENT_TIMESTAMP - data_hora_inicio
                            )
                        )
                    )::INTEGER
                )
            WHERE id = %s
              AND data_hora_fim IS NULL
            """,
            (acesso_id,)
        )

        atualizado = cursor.rowcount > 0
        conexao.commit()

        return atualizado

    except Exception as erro:
        conexao.rollback()
        print(f"Erro ao finalizar acesso: {erro}")
        return False

    finally:
        if cursor:
            cursor.close()
        conexao.close()


# ==================================================
# RESUMO DOS INDICADORES DO DASHBOARD
# ==================================================

def obter_resumo_dashboard(periodo=30):

    conexao = conectar()

    if conexao is None:
        return None

    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM reconhecimento
                    WHERE data_hora >=
                        CURRENT_TIMESTAMP - (%s * INTERVAL '1 day')
                ) AS total_reconhecimentos,

                (
                    SELECT COUNT(*)
                    FROM acessos
                    WHERE data_hora_inicio >=
                        CURRENT_TIMESTAMP - (%s * INTERVAL '1 day')
                ) AS total_acessos,

                (
                    SELECT COALESCE(SUM(tempo_uso), 0)
                    FROM acessos
                    WHERE data_hora_inicio >=
                        CURRENT_TIMESTAMP - (%s * INTERVAL '1 day')
                ) AS tempo_total,

                (
                    SELECT ROUND(AVG(confianca)::NUMERIC, 4)
                    FROM reconhecimento
                    WHERE data_hora >=
                        CURRENT_TIMESTAMP - (%s * INTERVAL '1 day')
                ) AS confianca_media,

                (
                    SELECT COUNT(*)
                    FROM erros
                    WHERE data_hora >=
                        CURRENT_TIMESTAMP - (%s * INTERVAL '1 day')
                ) AS total_erros
            """,
            (periodo, periodo, periodo, periodo, periodo)
        )

        resultado = cursor.fetchone()

        return {
            "total_reconhecimentos": resultado[0] or 0,
            "total_acessos": resultado[1] or 0,
            "tempo_total_segundos": resultado[2] or 0,
            "confianca_media": float(resultado[3] or 0),
            "total_erros": resultado[4] or 0,
        }

    except Exception as erro:
        print(f"Erro ao obter resumo do dashboard: {erro}")
        return None

    finally:
        if cursor:
            cursor.close()
        conexao.close()


# ==================================================
# SINAIS MAIS RECONHECIDOS
# ==================================================

def obter_ranking_sinais(periodo=30):

    conexao = conectar()

    if conexao is None:
        return None

    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT
                s.nome,
                COUNT(r.id) AS quantidade
            FROM sinais s
            LEFT JOIN reconhecimento r
                ON r.sinal_id = s.id
                AND r.data_hora >=
                    CURRENT_TIMESTAMP - (%s * INTERVAL '1 day')
            WHERE s.ativo = TRUE
            GROUP BY s.id, s.nome
            ORDER BY quantidade DESC, s.nome ASC
            """,
            (periodo,)
        )

        resultados = cursor.fetchall()

        return [
            {
                "sinal": linha[0],
                "quantidade": linha[1]
            }
            for linha in resultados
        ]

    except Exception as erro:
        print(f"Erro ao obter ranking dos sinais: {erro}")
        return None

    finally:
        if cursor:
            cursor.close()
        conexao.close()


# ==================================================
# EVOLUÇÃO DIÁRIA DOS RECONHECIMENTOS
# ==================================================

def obter_evolucao_diaria(periodo=30):

    conexao = conectar()

    if conexao is None:
        return None

    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT
                dias.dia::DATE AS data,
                COUNT(r.id) AS quantidade
            FROM generate_series(
                CURRENT_DATE - (%s - 1),
                CURRENT_DATE,
                INTERVAL '1 day'
            ) AS dias(dia)
            LEFT JOIN reconhecimento r
                ON r.data_hora >= dias.dia
                AND r.data_hora < dias.dia + INTERVAL '1 day'
            GROUP BY dias.dia
            ORDER BY dias.dia
            """,
            (periodo,)
        )

        resultados = cursor.fetchall()

        return [
            {
                "data": linha[0].isoformat(),
                "quantidade": linha[1]
            }
            for linha in resultados
        ]

    except Exception as erro:
        print(f"Erro ao obter evolução diária: {erro}")
        return None

    finally:
        if cursor:
            cursor.close()
        conexao.close()


# ==================================================
# RECONHECIMENTOS RECENTES
# ==================================================

def obter_reconhecimentos_recentes(limite=10):

    conexao = conectar()

    if conexao is None:
        return None

    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT
                s.nome,
                r.confianca,
                r.data_hora
            FROM reconhecimento r
            INNER JOIN sinais s
                ON s.id = r.sinal_id
            ORDER BY r.data_hora DESC
            LIMIT %s
            """,
            (limite,)
        )

        resultados = cursor.fetchall()

        return [
            {
                "sinal": linha[0],
                "confianca": float(linha[1]),
                "data_hora": linha[2].isoformat()
            }
            for linha in resultados
        ]

    except Exception as erro:
        print(f"Erro ao obter reconhecimentos recentes: {erro}")
        return None

    finally:
        if cursor:
            cursor.close()
        conexao.close()


# ==================================================
# HISTÓRICO RECENTE DE ACESSOS
# ==================================================

def obter_acessos_recentes(limite=10):

    conexao = conectar()

    if conexao is None:
        return None

    cursor = None

    try:
        cursor = conexao.cursor()

        cursor.execute(
            """
            SELECT
                id,
                data_hora_inicio,
                data_hora_fim,
                tempo_uso
            FROM acessos
            ORDER BY data_hora_inicio DESC
            LIMIT %s
            """,
            (limite,)
        )

        resultados = cursor.fetchall()

        return [
            {
                "id": linha[0],
                "inicio": linha[1].isoformat() if linha[1] else None,
                "fim": linha[2].isoformat() if linha[2] else None,
                "tempo_uso_segundos": linha[3]
            }
            for linha in resultados
        ]

    except Exception as erro:
        print(f"Erro ao obter acessos recentes: {erro}")
        return None

    finally:
        if cursor:
            cursor.close()
        conexao.close()
